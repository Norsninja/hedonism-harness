# v0.43 — chamber-wide food-redistribution intervention (substrate causal probe)

**Status:** pre-registered 2026-05-07; **HALTED PRE-SWEEP 2026-05-07**
on substrate feasibility finding (see SUBSTRATE_PREFLIGHT_HALT
addendum below). Sweep + audit not executed. Replacement pre-reg
(v0.43R candidate) pending feasibility probe at multiple ticks +
density-reduction variant.
**Date:** 2026-05-07
**Branch:** `claude/v0.43-resource-flattening-intervention`
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
reframed as one-off n=8 noise excursion), v0.42 (first causal probe
— **MECHANISM_NOT_NECESSARY**; tick-50 leader hard kill at
tick-50/tick-51 boundary did not collapse post-50 dominance; the
pattern reconstitutes through another surviving lineage; causal
search pivots from lineage identity to substrate structure).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

## Question

v0.42 ruled out the tick-50 leader's identity as a necessary causal
carrier of post-50 dominance under hard-kill removal. The dominance
pattern reconstitutes through another surviving lineage. The locked
v0.42 phrase named the next move:

> v0.43 candidate: pivot to substrate-level interventions (resource
> concentration shock, hazard relocation) rather than lineage-level
> interventions.

The active question for v0.43 is:

> **Is the chamber's resource concentration structure NECESSARY for
> the post-50 dominance pattern? If we destroy the food zone at the
> tick-50/tick-51 boundary by uniformly redistributing existing food
> across all eligible chamber cells, does post-50 dominance fail to
> reconstitute, or does it persist regardless of substrate
> concentration?**

This is a **substrate-level necessity probe**, parallel in cadence
to v0.42 but operating on the food layer rather than the agent
layer. The hard-kill design from v0.42 is reused conceptually: the
cleanest causal intervention is the most disruptive one (uniform
flattening), with a multiset-preserving permutation as the
size-matched control.

If post-50 dominance collapses under flattening but not under
multiset-preserving permutation, **resource concentration as such
is necessary** for the v0.34..v0.41 pattern. If both interventions
disrupt comparably, the system is sensitive to **any food-substrate
rewrite**, not specifically to concentration destruction. If
neither disrupts, the causal source lies further upstream than the
food-zone substrate (hazard topology, chamber geometry, founder-
trait + spatial-position interaction, birth-position constraints).

This is the **second sim-mechanics change** in the science arc since
v0.27. v0.42 introduced the intervention hook + agent-kill kinds;
v0.43 extends `core/interventions.py` with two substrate-rewrite
kinds (`flatten_food_at_tick50`, `shuffle_food_at_tick50`) without
modifying the existing `kill_tick50_leader` /
`kill_size_matched_nonleader` paths. The chamber-driver hook
already in place from v0.42 is reused unchanged.

## What this slice tests, and what it does NOT test

### Tests

- Whether **`post_intervention_top_lineage_b50_share`** (the same
  primary observable as v0.42) in the chamber-wide flatten arm B
  drops by ≥ 0.15 relative to the null arm A at h=8, AND the
  multiset-preserving shuffle arm C remains within ±0.10 of arm A
  at h=8. **This is the primary substrate-necessity test.**
- Whether the B-vs-A reduction is larger at h=8 than at h=0
  (secondary observable; tests hazard-amplification specificity of
  the substrate-necessity effect).
- Whether the intervention's `FoodRedistributedByIntervention`
  summary events are emitted exactly once per intervention-firing
  run, with the correct `intervention_kind`, `total_food_before`,
  `total_food_after`, and `n_cells_changed` fields.
- Whether the intervention preserves total food mass within float-
  tolerance (B and C), and whether C additionally preserves the
  multiset of `food_value` across eligible cells.
- Whether the **default-None intervention path** continues to be
  byte-identical to pre-v0.42 behaviour, AND whether the
  `kind="null"` path remains byte-identical to v0.42's null path.
- Whether the auxiliary finding **FLATTEN_ABLATES_REPRODUCTION**
  fires per-hazard: B_flatten produced > 2 of 8 runs with zero
  post-50 surviving-lineage births at any hazard.

### Does NOT test

- **Mechanism sufficiency.** This slice tests substrate necessity
  only. Sufficiency would require constructing a new substrate from
  scratch and asking whether dominance emerges; deferred indefinitely.
- **Mechanism specificity** (which property of the food substrate
  carries the effect). v0.43 cannot distinguish food-density,
  foraging-path geometry, hazard-adjacent niche structure, or
  birth-clustering effects. Refinement interventions are reserved
  for v0.44+ conditional on v0.43 firing.
- **Hazard generalisation.** Only h=0 and h=8 are tested. h=4 and
  h=12 are reserved for v0.44+ if the v0.43 result motivates
  hazard-grid expansion.
- **Cross-stream calibration of the intervention.** v0.43 runs only
  seeds 49..56 (one stream). If v0.43 fires, calibrating on a
  second seed band is a v0.44+ candidate. (See also v0.42's
  deferred candidate (j) — cross-stream calibration of v0.42's
  null result. Both calibrations are v0.44+ candidates.)
- **The v0.34..v0.42 corpus.** The five-stream + v0.42 intervention
  corpus is sealed and unchanged. v0.43 does NOT re-run any prior
  reducer.
- **Hazard topology disruption.** The intervention preserves
  HAZARD-cell positions and counts. Hazard-relocation interventions
  are reserved for v0.44+ candidate (h).
- **Wall-cell modifications.** Walls are inviolate; flatten and
  shuffle skip them.
- **Magnitude framing as "spread" or "amplification".** v0.43's
  primary uses absolute-share differences at h=8, NOT a hazard-axis
  spread (mean(h=12) − mean(h=0)) like v0.34..v0.41 used. The
  secondary explicitly compares B-vs-A reductions across h=0 and
  h=8 instead. (Same convention as v0.42.)

### Deferred (v0.44+ candidates, conditional on v0.43 outcome)

- **If RESOURCE_CONCENTRATION_NECESSARY fires** (B collapses; C does
  not). v0.44 candidates: (a) hazard-grid expansion; (b) intervention-
  type refinement (partial flatten, restricted-region flatten,
  density-only vs position-only) to identify which property of
  concentration carries the effect; (c) sufficiency probe (build
  concentration on a previously-uniform substrate); (d) cross-stream
  calibration on seed band 57..64.
- **If SUBSTRATE_REWRITE_DISRUPTS_DOMINANCE fires** (B and C both
  collapse; any substrate rewrite disrupts the pattern). v0.44
  candidate: refine the control to test whether smaller / partial
  rewrites also disrupt, or whether the pattern is robust to small
  perturbations and only fragile to large ones. Mechanism is
  "substrate-shock-fragile," not "concentration-specific."
- **If RESOURCE_CONCENTRATION_NOT_NECESSARY fires** (B does not
  collapse; the pattern persists through full substrate flattening).
  v0.44 candidate: hazard relocation (h) — the next plausible
  substrate-anchored property. Concentration is ruled out at the
  food-layer level; the causal source is further upstream
  (hazard topology, chamber geometry, founder-trait + spatial-
  position interaction, birth-position constraints).
- **If FLATTEN_ABLATES_REPRODUCTION fires per-hazard** (auxiliary,
  not exclusive of the primary verdict). The flatten intervention
  reduced per-cell food density below the per-pickup viability
  threshold, ablating reproduction itself. v0.44 candidate:
  reduce the flatten's dilution factor (e.g., flatten over a
  smaller region) to separate "concentration matters for dominance"
  from "concentration matters for reproduction at all."

### Quarantined (not v0.43 inputs)

- v0.34..v0.42 reducer outputs. These remain on disk but are not
  re-read by v0.43's audit. v0.43's primary observable is computed
  from v0.43's own sweep events.jsonl (parallel to v0.42).
- HedonismPolicy comparisons. Deferred indefinitely.
- Mesa migration. Closed indefinitely.
- v0.36 founder-trait observables. Orthogonal.
- Cross-stream calibration of v0.42 (deferred candidate (j) from
  v0.42 close). Reserved for v0.44+.

## Conservation framing — second `src/` modification since v0.27

v0.43 modifies `src/` for the second time in the v0.34..v0.43 arc
(v0.42 was the first). The modifications are strictly additive
relative to v0.42:

- **Modified module:** `src/hedonism_harness/core/interventions.py`
  - Two new `kind` literal values: `"flatten_food_at_tick50"`,
    `"shuffle_food_at_tick50"`.
  - Two new selection / rewrite functions:
    `_flatten_food_over_eligible_cells`,
    `_shuffle_food_over_eligible_cells`.
  - Extended `apply_intervention` dispatcher to route the new kinds.
  - The existing `null` / `kill_tick50_leader` /
    `kill_size_matched_nonleader` paths remain byte-identical.
- **New event type:** added to the central event spec
  (`core/events.py`).
  - `FoodRedistributedByIntervention(intervention_kind,
    intervention_tick, effective_tick, total_food_before,
    total_food_after, n_cells_changed, n_eligible_cells)`.
  - Purely additive; no agent deaths emitted. **No new
    `DeathCause` enum value** (parallel to v0.42's discipline:
    add cause values only when biologically motivated).
- **No new chamber-runner hook.** The v0.42 hook
  (`optional_intervention: InterventionConfig | None = None` on
  `run_chamber`) is reused unchanged. The new kinds dispatch
  through the existing `apply_intervention` entry point.

The following are NOT modified:

- Existing chamber, policy, or population-dynamics behaviour outside
  the new intervention `kind` paths. Default
  `optional_intervention=None` and `kind="null"` remain byte-
  identical to pre-v0.42 / v0.42 behaviour.
- `src/hedonism_harness/policies/gradient_policy.py`,
  `src/hedonism_harness/policies/hedonism_policy.py`. No policy
  changes.
- `src/hedonism_harness/experiments/comparison_grid.py` arm tuples
  (V0_25_ARMS, V0_27_ARMS, V0_31_TIGHT_W_ARMS, V0_32_TIGHT_H_ARMS,
  V0_33_TIGHT_H_ARMS, V0_39_TIGHT_H_ARMS, V0_41_TIGHT_H_ARMS,
  V0_42_INTERVENTION_ARMS). One new constant
  `V0_43_INTERVENTION_ARMS` is added (additive only).
- All v0.34..v0.42 reducer scripts and audits. Byte-identical
  before and after v0.43.
- Pre-v0.43 events on disk. Re-running prior sweeps with default
  `optional_intervention=None` or `kind="null"` produces byte-
  identical events.jsonl files (regression-guarded invariant
  inherited from v0.42; extended in v0.43 by sampling a v0.42
  A_null seed re-run).
- The `kill_tick50_leader` and `kill_size_matched_nonleader` paths
  are byte-identical: the v0.42 sweep can be re-run end-to-end on
  v0.43's branch and produces byte-identical events.jsonl files
  (regression test H2e).
- Wall and hazard cells: positions and counts unchanged by either
  new intervention kind (substrate-conservation invariant in audit).

## Mechanism

v0.43 ships:

1. Two new intervention kinds in
   `src/hedonism_harness/core/interventions.py` (extension only).
2. One new event type in `src/hedonism_harness/core/events.py`.
3. A new sweep driver and arm tuple.
4. A v0.43 audit reducer that consumes the v0.43 sweep events.
5. Paired test files for each addition.
6. This pre-reg.
7. A new manifest doc post-Results.

### 1. Intervention extensions (`src/hedonism_harness/core/interventions.py`)

The existing `InterventionConfig.kind` Literal is extended to:

```python
kind: Literal[
    "null",
    "kill_tick50_leader",
    "kill_size_matched_nonleader",
    "flatten_food_at_tick50",       # NEW v0.43
    "shuffle_food_at_tick50",       # NEW v0.43
]
```

Two new pure-function helpers select the **eligible-cell set** at
the tick-50/tick-51 boundary and apply the rewrite:

```python
def _eligible_cells(world) -> list[tuple[int, int]]:
    """Cells with kind in {EMPTY, FOOD} at tick 50, sorted by (x, y)
    ascending. Excludes HAZARD and WALL cells. Pure function of
    world.kind_layer at firing time. No RNG."""

def _flatten_food_over_eligible_cells(world) -> InterventionResult:
    """B arm. Compute total_food = sum(food_value over eligible).
    Compute mean = total_food / len(eligible). For every eligible
    cell: food_value <- mean; kind <- FOOD if mean > 0 else EMPTY.
    Hazard and wall cells unchanged. Total food preserved within
    float-32 tolerance."""

def _shuffle_food_over_eligible_cells(world) -> InterventionResult:
    """C arm. Take values_old = [food_value[c] for c in eligible
    sorted by (x, y)]. Take values_new = list(reversed(values_old)).
    For i, c in enumerate(eligible): food_value[c] <- values_new[i];
    kind[c] <- FOOD if values_new[i] > 0 else EMPTY. Hazard and wall
    cells unchanged. Total food and multiset of food values
    exactly preserved."""
```

The dispatcher:

```python
def apply_intervention(world, config) -> InterventionResult:
    if config.kind == "null":
        return InterventionResult(fired=False, ...)
    if config.kind == "kill_tick50_leader":
        return _kill_leader(world, ...)               # v0.42 path, unchanged
    if config.kind == "kill_size_matched_nonleader":
        return _kill_smnonleader(world, ...)          # v0.42 path, unchanged
    if config.kind == "flatten_food_at_tick50":       # NEW v0.43
        return _flatten_food_over_eligible_cells(world)
    if config.kind == "shuffle_food_at_tick50":       # NEW v0.43
        return _shuffle_food_over_eligible_cells(world)
    raise ValueError(f"Unknown kind: {config.kind}")
```

Selection rules:

- **`flatten_food_at_tick50` (B arm)**: at tick 50 close, eligible-
  cell set is computed; total food is summed over it; mean is
  written to every eligible cell. `kind` is updated to FOOD
  wherever `mean > 0` and to EMPTY otherwise. Total food preserved
  within float-32 tolerance. Hazard and wall cells unchanged.
- **`shuffle_food_at_tick50` (C arm)**: at tick 50 close, eligible-
  cell set is computed and sorted by `(x, y)` ascending; the
  ordered vector of `food_value` is reversed; reversed values are
  written back in `(x, y)` order. `kind` is updated cell-by-cell:
  FOOD where the reassigned value is positive, EMPTY otherwise.
  Total food and multiset of food values exactly preserved.
  Hazard and wall cells unchanged.

Determinism contract:

- Both new kinds are pure functions of tick-50 chamber state. No
  new RNG. No `model.streams` draws.
- For a given (seed, hazard, intervention_kind), the intervention
  produces the same post-state every time.
- Reverse-row-major shuffle is a fixed permutation over the
  `(x, y)`-sorted eligible-cell sequence; trivially reproducible.

### 2. Event spec extension (`src/hedonism_harness/core/events.py`)

One new frozen dataclass:

```python
@dataclass(frozen=True)
class FoodRedistributedByIntervention:
    intervention_kind: str          # "flatten_food_at_tick50" | "shuffle_food_at_tick50"
    intervention_tick: int          # 50
    effective_tick: int             # 51
    n_eligible_cells: int           # cells with kind in {EMPTY, FOOD} at tick 50
    n_cells_changed: int            # cells whose food_value or kind changed
    total_food_before: float        # sum of food_value over eligible cells before
    total_food_after: float         # sum of food_value over eligible cells after
    eligible_cells_digest: str      # SHA-256 hex of (x, y) pairs over eligible cells, sorted ascending; chamber-geometry anchor
    food_multiset_digest_before: str  # SHA-256 hex of struct-packed float32 food_value vector over eligible cells, sorted ascending (before)
    food_multiset_digest_after: str   # SHA-256 hex of struct-packed float32 food_value vector over eligible cells, sorted ascending (after)
```

Digest format (locked): for the food multiset, sort the float32
`food_value` vector over eligible cells in ascending order, pack
as little-endian float32 via `struct.pack(f"<{n}f", *sorted_vals)`,
SHA-256, hex-encode. For the cells digest, take the eligible cells
sorted by `(x, y)` ascending, encode as `b"\n".join(f"{x},{y}".encode()
for (x, y) in sorted_cells)`, SHA-256, hex-encode. Both digests are
pure functions of locked chamber state at firing time; reproducible.

Added to `_SIGNAL_NAMES` and `AnyEvent` union. **No new `DeathCause`
value.** No `AgentDied` events emitted by either new kind (no
agents are killed by the food redistribution itself; agents that
later starve will emit `AgentDied(cause=STARVATION)` through the
existing path).

The C arm's multiset-preservation invariant is verified at audit
time by asserting `food_multiset_digest_before ==
food_multiset_digest_after` on every fired C event. The B arm's
flatten does NOT preserve the multiset (by design); for B,
`food_multiset_digest_before != food_multiset_digest_after` is
expected (it's a flatten).

### 3. Sweep + arm tuple (`scripts/v0.43_sweep.py`,
   `src/hedonism_harness/experiments/comparison_grid.py` additions)

Three arms × 2 hazards × 8 seeds = **48 runs**. Arm tuple:

```python
V0_43_INTERVENTION_ARMS: tuple[Arm, ...] = (
    # A_null: no intervention (mirrors v0.42 A_null at h=0, h=8)
    Arm(label="v043-A_null-hzd0-influx-1.0",  hazard_damage=0.0, ..., intervention_kind="null"),
    Arm(label="v043-A_null-hzd8-influx-1.0",  hazard_damage=8.0, ..., intervention_kind="null"),
    # B_flatten_food
    Arm(label="v043-B_flatten_food-hzd0-influx-1.0",  hazard_damage=0.0, ..., intervention_kind="flatten_food_at_tick50"),
    Arm(label="v043-B_flatten_food-hzd8-influx-1.0",  hazard_damage=8.0, ..., intervention_kind="flatten_food_at_tick50"),
    # C_shuffle_food
    Arm(label="v043-C_shuffle_food-hzd0-influx-1.0", hazard_damage=0.0, ..., intervention_kind="shuffle_food_at_tick50"),
    Arm(label="v043-C_shuffle_food-hzd8-influx-1.0", hazard_damage=8.0, ..., intervention_kind="shuffle_food_at_tick50"),
)
```

Seeds: 49..56 (disjoint from v0.41's 33..40 and v0.42's 41..48).
All other substrate fields (chamber=tight_gradient,
ambient_influx_rate=1.0, n_ticks=200, n_founders=5) inherited from
v0.42 unchanged.

### 4. v0.43 audit (`scripts/v0_43_intervention_audit.py`)

Imports only `LineageReplayError` via `importlib.util` (project
standard halt class). Otherwise pure stdlib + `csv.DictReader` /
`json.loads`.

Reads:

- Per-arm `comparison.csv` files from
  `runs/fear-hunger-v0.43-tight_gradient/arms/`.
- Per-run `events.jsonl` files (specifically:
  `FoodRedistributedByIntervention` summary events + post-50
  `AgentBorn` events to compute the primary observable, parallel
  to v0.42's pattern).

Halt invariants (5):

- **H2a (run count):** exactly 6 arms × 8 seeds = 48 runs on disk.
- **H2b (intervention-fire count per arm):**
  - A_null arms: 0 `FoodRedistributedByIntervention` events per run.
  - B_flatten arms: exactly 1 event per run with
    `intervention_kind="flatten_food_at_tick50"`.
  - C_shuffle arms: exactly 1 event per run with
    `intervention_kind="shuffle_food_at_tick50"`.
- **H2c (effective_tick):** every fired event has
  `effective_tick=51`.
- **H2d (substrate conservation):**
  - For B and C: `abs(total_food_after - total_food_before) <=
    max(1e-3, 1e-5 * total_food_before)`.
  - For C: `food_multiset_digest_before ==
    food_multiset_digest_after` on every fired C event (digest
    equality verifies multiset preservation exactly without
    storing full snapshots).
  - For B: `food_multiset_digest_before !=
    food_multiset_digest_after` on every fired B event (flatten
    is not a permutation; multiset must change in non-degenerate
    cases). On any B run where the digests are equal AND
    `n_cells_changed > 0`, halt — indicates an arithmetic bug.
    (If `n_cells_changed == 0` on B, the substrate was already
    uniform pre-intervention; digests may match legitimately —
    record as descriptive but do not halt.)
  - For both: `eligible_cells_digest` is consistent across all 48
    runs at the same (hazard) bucket — chamber geometry is
    seed-independent at tick 50 (no agent action mutates kind for
    eligible-cell membership). Halt if drift detected.
  - For both: `n_eligible_cells` consistent with chamber geometry
    (computed from layout); `n_cells_changed <= n_eligible_cells`.
- **H2e (regression byte-identity):** sampled v0.42 A_null seed
  re-run with `optional_intervention=null` produces events.jsonl
  byte-identical to v0.42's sealed reference (regression on the
  v0.42 path). Sampled v0.42 B_kill_leader seed re-run produces
  events.jsonl byte-identical to v0.42's reference (regression on
  the existing kill paths). Halt if either fingerprint drifts.
- **C-rises-above-A halt:** if `c_share_h8 > a_share_h8 + 0.10`,
  halt loud. Substrate artefact unmodeled at pre-reg time.

Computes per-(arm, seed) — **identical observable to v0.42**:

- `post_intervention_top_lineage_b50_share` =
  count_of_post_50_AgentBorn(top_lineage_post50) /
  count_of_post_50_AgentBorn(all_lineages).

  For v0.43, no lineage is killed by the intervention, so all 5
  founder lineages are eligible to be the "top" post-50 lineage.
  "Top lineage post 50" = the lineage with the most post-50 births;
  if tie, lowest lineage_id. NaN if total_post_50_births_all == 0
  (run excluded; counted in `n_excluded_zero_post50`).
- `total_post_50_births` (for context).
- `intervention_kind`, `n_cells_changed`, `total_food_before`,
  `total_food_after` (from event).

Aggregates per-(arm, hazard) and computes the locked decision rule.

Outputs eight CSVs under `runs/lineage-v0.43/`:

- `per_run.csv` — 48 rows: arm, hazard, seed, fired,
  intervention_kind, n_eligible_cells, n_cells_changed,
  total_food_before, total_food_after, total_post_50_births,
  top_lineage_post50_births, top_lineage_id,
  post_intervention_top_lineage_b50_share, excluded_zero_post50.
- `per_arm_per_hazard.csv` — 6 rows: arm, hazard, n_runs, n_used,
  n_excluded_zero_post50, mean_share, median_share.
- `intervention_summary.csv` — 6 rows: arm, hazard,
  mean_post_intervention_top_lineage_b50_share, n_runs_used.
- `primary_test.csv` — 1 row: a_share_h8, b_share_h8, c_share_h8,
  delta_b_minus_a_h8, delta_c_minus_a_h8, b_passes (b−a ≤ −0.15),
  c_passes (|c−a| ≤ 0.10), c_below_a (c−a ≤ −0.10),
  c_above_a (c−a > 0.10), resource_concentration_necessary,
  substrate_rewrite_disrupts, resource_concentration_not_necessary,
  c_above_a_unmodeled_substrate_artefact, primary_fires, verdict.
- `secondary_test.csv` — 1 row: delta_b_minus_a_h0,
  delta_b_minus_a_h8, hazard_amplified
  (|delta_h8| > |delta_h0|), secondary_fires.
- `verdict.csv` — 1 row: verdict, locked_phrase,
  resource_concentration_necessary, substrate_rewrite_disrupts,
  resource_concentration_not_necessary, primary_fires,
  secondary_fires.
- `auxiliary_findings.csv` — 2 rows (one per hazard):
  hazard, b_n_excluded_zero_post50, ablation_threshold_exceeded
  (`b_n_excluded > 2`), auxiliary_phrase_fires.
- `byte_identity_anchor.csv` — 2 rows: regression-guard sample
  seeds (one v0.42 A_null + one v0.42 B_kill_leader), expected
  fingerprint, observed fingerprint, anchor_ok.

### Locked constants

```python
EXPECTED_HAZARDS: tuple[int, ...] = (0, 8)
EXPECTED_SEEDS: tuple[int, ...] = tuple(range(49, 57))  # 49..56
EXPECTED_N_FOUNDERS: int = 5
EXPECTED_N_TICKS: int = 200
EXPECTED_INTERVENTION_TICK: int = 50
EXPECTED_EFFECTIVE_TICK: int = 51
EXPECTED_RUNS_TOTAL: int = 48  # 6 arms x 8 seeds

# Locked thresholds (parallel to v0.42)
PRIMARY_B_REDUCTION_THRESHOLD: float = 0.15  # B share <= A share - 0.15
PRIMARY_C_TOLERANCE: float = 0.10            # |C share - A share| <= 0.10

# Auxiliary threshold
AUXILIARY_FLATTEN_ABLATION_MAX_EXCLUDED: int = 2  # > 2 of 8 fires aux phrase

# Substrate conservation tolerance
TOTAL_FOOD_ABS_TOL: float = 1e-3
TOTAL_FOOD_REL_TOL: float = 1e-5
MULTISET_ELEMENT_TOL: float = 1e-6

# Arm labels
ARM_A_NULL: str = "v043-A_null"
ARM_B_FLATTEN: str = "v043-B_flatten_food"
ARM_C_SHUFFLE: str = "v043-C_shuffle_food"

# Intervention kind labels (extends v0.42)
KIND_NULL: str = "null"
KIND_FLATTEN: str = "flatten_food_at_tick50"
KIND_SHUFFLE: str = "shuffle_food_at_tick50"

# Cell-kind eligibility
ELIGIBLE_KINDS: frozenset = frozenset({"EMPTY", "FOOD"})  # by name
```

### Determinism — anchors

- v0.21..v0.42 events.jsonl + sidecar artifacts are not re-read by
  the **primary** v0.43 audit. The H2e regression check **does**
  read selected sealed v0.42 reference events.jsonl files (one
  v0.42 A_null seed + one v0.42 B_kill_leader seed) for fingerprint
  comparison only; it does not consume them as scientific inputs.
- v0.21..v0.42 test suites continue to pass (additive guard).
- Default `optional_intervention=None` is byte-identical to
  pre-v0.42 behaviour — re-running any pre-v0.42 sweep produces
  byte-identical events.jsonl files.
- `optional_intervention=InterventionConfig(kind="null")` is byte-
  identical to default-None behaviour (regression test).
- v0.42's `kill_tick50_leader` and `kill_size_matched_nonleader`
  paths produce byte-identical events.jsonl files when re-run on
  v0.43's branch (H2e).
- All v0.34..v0.42 reducer modules are imported only insofar as the
  v0.43 audit needs `LineageReplayError`. **No mutation of any
  pre-v0.43 module.**

### Wall-time estimate

- v0.43 sweep: ~13s (2 hazards × 3 arms × 8 seeds = 48 runs at
  locked parameters; comparable to v0.42's 48-run sweep at ~13s).
  Note: the flatten arm may cause earlier population collapse in
  some seeds, slightly reducing per-run wall time.
- v0.43 audit: ~3s on the 48-row aggregate plus events.jsonl
  parsing for the 48 runs.
- **Total v0.43 incremental wall-time:** ~16s.

## Observables — pre-committed before reading the data

### Per-run — 48 rows total

- `arm` ∈ {A_null, B_flatten_food, C_shuffle_food}.
- `hazard` ∈ {0, 8}.
- `seed` ∈ {49..56}.
- `fired`: bool. True iff a `FoodRedistributedByIntervention`
  event was emitted for this run. False for A_null. Note: B/C
  runs may legitimately have `fired=True` with `n_cells_changed=0`
  in edge cases (already-uniform food before flatten; reverse
  permutation that happens to fix all values). Firing is event-
  emission, not outcome.
- `intervention_kind`: str. The kind label.
- `n_eligible_cells`: int. Count of cells with kind in {EMPTY, FOOD}
  at tick 50.
- `n_cells_changed`: int. Count of cells whose `food_value` or
  `kind` changed.
- `total_food_before`, `total_food_after`: float. Conservation
  pair.
- `total_post_50_births`: int. Count of `AgentBorn` events with
  `tick > 50` in this run, across all 5 lineages (no lineage
  exclusion in v0.43, since no lineage is killed).
- `top_lineage_id`: int. Lineage with the most post-50 births
  (tie-break: lowest lineage_id).
- `top_lineage_post50_births`: int.
- `post_intervention_top_lineage_b50_share`: float in [0, 1].
  `top_lineage_post50_births / total_post_50_births`. NaN if
  `total_post_50_births == 0` (run excluded; counted in
  `n_excluded_zero_post50`).
- `excluded_zero_post50`: bool.

### Per-(arm, hazard) — 6 rows total

- `mean_post_intervention_top_lineage_b50_share` over the 8 runs in
  the bucket, excluding NaN runs.
- `n_runs_used`: number of runs contributing to the mean.
- `n_excluded_zero_post50`: NaN excluded.

### Primary test (`primary_test.csv` — 1 row)

- `a_share_h8`, `b_share_h8`, `c_share_h8`.
- `delta_b_minus_a_h8 := b_share_h8 - a_share_h8`.
- `delta_c_minus_a_h8 := c_share_h8 - a_share_h8`.
- `b_passes := delta_b_minus_a_h8 <= -PRIMARY_B_REDUCTION_THRESHOLD`
  (i.e., B share is at least 0.15 BELOW A share).
- `c_passes := abs(delta_c_minus_a_h8) <= PRIMARY_C_TOLERANCE`
  (i.e., C share is within ±0.10 of A share).
- `c_below_a := delta_c_minus_a_h8 <= -PRIMARY_C_TOLERANCE`
  (C drops below A by more than 0.10).
- `c_above_a := delta_c_minus_a_h8 > PRIMARY_C_TOLERANCE`
  (C rises above A by more than 0.10 — substrate-artefact halt).
- `resource_concentration_necessary := b_passes AND c_passes`.
- `substrate_rewrite_disrupts := b_passes AND c_below_a`.
- `resource_concentration_not_necessary := NOT b_passes`.
- `c_above_a_unmodeled_substrate_artefact := b_passes AND c_above_a`
  (halt cell — audit halts loud; verdict is NOT emitted).
- `primary_fires := resource_concentration_necessary OR
  substrate_rewrite_disrupts` (umbrella for verdict-firing cases;
  the halt cell does NOT count as a fire).
- `verdict`: derived from the explicit booleans above (see Decision
  rules).

### Secondary test (`secondary_test.csv` — 1 row)

- `delta_b_minus_a_h0`, `delta_b_minus_a_h8`.
- `hazard_amplified := abs(delta_b_minus_a_h8) > abs(delta_b_minus_a_h0)`.
- `secondary_fires := primary_fires AND hazard_amplified`.

### Auxiliary findings (`auxiliary_findings.csv` — 2 rows, one per hazard)

- `hazard`.
- `b_n_excluded_zero_post50`: number of B_flatten runs at this
  hazard with zero post-50 births (out of 8).
- `ablation_threshold_exceeded := b_n_excluded > AUXILIARY_FLATTEN_ABLATION_MAX_EXCLUDED`
  (i.e., > 2 of 8).
- `auxiliary_phrase_fires`: bool.

The auxiliary finding is **non-exclusive** of the primary verdict
— both can fire simultaneously, both are reported in Results.

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (additive `src/` modification).** Only the new intervention
  kinds, new event class, and one new arm constant. All pre-v0.42
  default-None paths and v0.42 kill paths are byte-identical.
  **Includes regression tests on a sampled v0.42 A_null seed AND
  a sampled v0.42 B_kill_leader seed.**
- **H2a (run count).** Exactly 48 runs on disk after v0.43 sweep.
- **H2b (intervention-fire count per arm).** A_null: 0 fires per
  run. B: exactly 1 flatten event per run. C: exactly 1 shuffle
  event per run.
- **H2c (effective_tick).** Every `FoodRedistributedByIntervention`
  event has `effective_tick=51`.
- **H2d (substrate conservation).**
  - For B and C: total food preserved within float tolerance.
  - For C: multiset of `food_value` over eligible cells exactly
    preserved.
  - For both: HAZARD and WALL cell positions and counts unchanged
    by the intervention.
- **H2e (regression byte-identity).** Sampled v0.42 A_null seed
  AND v0.42 B_kill_leader seed re-run with v0.43 code produce
  events.jsonl byte-identical to v0.42's sealed references. Halt
  if either fingerprint drifts.
- **H3 (additive guard).** v0.21..v0.42 prior tests still pass
  after v0.43 additions.
- **H4 (no mutation of pre-v0.43 surface).** All pre-v0.43
  scripts, reducers, audits, pre-v0.43 arm tuples in
  [[src/hedonism_harness/experiments/comparison_grid.py]],
  chamber / population / policy modules — byte-identical before
  and after v0.43 (modulo the additive intervention kinds + arm
  constant + event class).

### Cautious form — three-way verdict on v0.43's substrate-necessity question

The verdict is intentionally three-way, mutually exclusive on the
locked decision space, plus one halt cell:

**RESOURCE_CONCENTRATION_NECESSARY.** **FIRES iff** `b_passes ==
True` AND `c_passes == True` (i.e., B share ≤ A share − 0.15 at
h=8, AND |C share − A share| ≤ 0.10 at h=8). Headline: destroying
the food zone via uniform redistribution materially disrupts post-50
dominance, while preserving the food multiset (relocating
concentration to a different chamber position) does not. Resource
concentration as such is **necessary** for the v0.34..v0.41 dominance
pattern under the tested substrate; the specific *location* of
concentration is not.

**SUBSTRATE_REWRITE_DISRUPTS_DOMINANCE.** **FIRES iff** `b_passes ==
True` AND `c_below_a == True` (B drops AND C drops by ≥ 0.10 below
A). Headline: both interventions disrupt post-50 dominance.
Concentration-as-such is not separable from generic substrate-rewrite
shock; the dominance pattern is fragile to **any** food-substrate
intervention of comparable magnitude.

**RESOURCE_CONCENTRATION_NOT_NECESSARY.** **FIRES iff** `b_passes ==
False`. Headline: destroying the food zone does not materially
disrupt post-50 dominance; some lineage reconstitutes the pattern
even on a uniform-food substrate. Resource concentration as
instantiated in tight_gradient is **not necessary** for the pattern;
the causal source is further upstream than the food layer (hazard
topology, chamber geometry, founder-trait + spatial-position
interaction, birth-position constraints).

**C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT (halt cell):** `b_passes ==
True` AND `c_above_a == True`. Substrate artefact unmodeled at
pre-reg time. Audit halts loud (`LineageReplayError`); no
scientific verdict is emitted.

(All four cells exhaust the rule space:
- `b_passes=True, c_passes=True` → CONCENTRATION_NECESSARY.
- `b_passes=True, c_below_a=True` → REWRITE_DISRUPTS.
- `b_passes=True, c_above_a=True` → C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT (halt).
- `b_passes=False, *` → CONCENTRATION_NOT_NECESSARY.)

### Auxiliary finding — independent of primary verdict

**FLATTEN_ABLATES_REPRODUCTION (per-hazard).** **FIRES iff**
`b_n_excluded_zero_post50 > 2` at any hazard. Reported alongside
the primary verdict; does NOT alter the verdict logic. Headline:
chamber-wide food flattening reduced per-cell food density below
the threshold required to sustain post-50 reproduction in this
fraction of seeds at this hazard. This is a **descriptive substrate
finding** with mechanistic content of its own: dilution alone can
ablate reproduction.

### Locked phrases for each verdict

> **RESOURCE_CONCENTRATION_NECESSARY phrase:** "Chamber-wide
> uniform flattening of food across all eligible cells at the
> tick-50/tick-51 boundary materially disrupts the post-50
> dominance pattern at h=8: when concentration is destroyed, the
> surviving lineages do not reconstitute concentration of comparable
> share. The multiset-preserving location-shuffle control (which
> preserves the food multiset but reverses position assignment via
> deterministic row-major reversal) does NOT produce comparable
> disruption. Under the tested substrate, **resource concentration
> as such is necessary** for the v0.34..v0.41 dominance pattern;
> the specific *location* of concentration in the chamber is not.
> v0.43 does not declare which property of concentration carries
> the effect (food density, foraging-path geometry, hazard-adjacent
> niche structure, birth-clustering effects); refinement
> interventions in v0.44+ are required. Necessity is established at
> one hazard level (h=8) on one seed band (49..56); cross-stream
> calibration is reserved for v0.44+. Sufficiency is NOT tested."

> **SUBSTRATE_REWRITE_DISRUPTS_DOMINANCE phrase:** "Chamber-wide
> uniform flattening of food disrupts post-50 dominance at h=8, but
> the multiset-preserving location-shuffle control produces
> comparable disruption. The post-50 dominance pattern is sensitive
> to **any food-substrate rewrite of comparable magnitude**, not
> specifically to concentration destruction. v0.34..v0.41's
> correlational pattern reflects a fragility to substrate-shock
> generally rather than a concentration-specific causal mechanism.
> v0.44 candidate: refine the control set to test whether smaller /
> partial substrate rewrites (e.g., shift only a subset of food
> cells; flatten only within the original food zone) also disrupt,
> or whether the dominance pattern is robust to small substrate
> perturbations and only fragile to large ones. Mechanism remains
> unidentified at the resource-concentration level."

> **RESOURCE_CONCENTRATION_NOT_NECESSARY phrase:** "Chamber-wide
> uniform flattening of food at the tick-50/tick-51 boundary does
> not materially disrupt the post-50 dominance pattern at h=8. A
> surviving lineage reconstitutes concentration-of-share even after
> the food substrate's concentration structure is destroyed.
> **Resource concentration as instantiated in tight_gradient is
> not necessary** for post-50 dominance; the causal source lives
> further upstream than the food-zone substrate. v0.42 ruled out
> the tick-50 leader's identity; v0.43 rules out chamber-wide food
> concentration. The remaining substrate-anchored candidates:
> hazard topology, chamber geometry (wall-adjacency, reachability),
> founder-trait + spatial-position interaction at tick 50, and
> birth-position constraints. v0.44 candidate: hazard relocation
> intervention (h)."

> **FLATTEN_ABLATES_REPRODUCTION (auxiliary, per-hazard) phrase:**
> "At hazard h=N, the B_flatten arm produced > 2 of 8 runs with
> zero post-50 births: chamber-wide food redistribution ablated
> reproduction itself rather than relocating dominance. This is a
> **descriptive substrate finding** parallel to but independent of
> the share-based primary verdict: flattening the food zone
> reduces per-cell food density below the threshold required to
> sustain post-50 reproduction in this fraction of seeds at this
> hazard. The primary verdict is computed over n_used (non-
> excluded) runs; this auxiliary finding is reported alongside but
> does NOT alter the primary verdict logic. v0.44 candidate:
> reduce the flatten's dilution factor (e.g., flatten over a
> smaller region) to separate concentration-matters-for-dominance
> from concentration-matters-for-reproduction-at-all."

To be reused verbatim if the corresponding verdict / auxiliary
finding fires.

### Caveats — locked, must appear in Results

- **Per-arm n is 8.** Each arm × hazard mean is over 8 runs. The
  ±0.15 / ±0.10 thresholds are conservative on n=8 but not bullet-
  proof against noise excursions. v0.44 may increase n if v0.43
  lands borderline.
- **Necessity only.** v0.43 does NOT test sufficiency.
- **One seed band.** Seeds 49..56 only. Cross-stream calibration of
  the substrate intervention is a v0.44+ candidate. (Inheriting
  the v0.39 → v0.40 → v0.41 lesson.)
- **Two hazards only.** h=0 and h=8.
- **Hard substrate rewrite.** Both B (uniform flatten) and C
  (reverse-row-major shuffle) are maximally disruptive within
  their respective design intent. No biological-realism claim is
  made. Hard rewrite is the cleanest causal probe, not the most
  realistic.
- **Hazard topology preserved.** HAZARD-cell positions and counts
  are unchanged by either intervention. v0.43 does NOT test
  hazard-substrate causality; that is reserved for v0.44+
  candidate (h).
- **Walls inviolate.** WALL cells are never modified.
- **No respawn / position-targeted influx in tight_gradient.** The
  intervention's flat distribution persists indefinitely (no
  reconcentration mechanism). Influx in tight_gradient credits a
  global pool (no per-cell injection). This is a property of the
  v0.43 substrate; on chambers with respawn or targeted influx,
  the intervention would be transient and the pre-reg would
  require revision.
- **No mechanism declaration even on the strongest outcome.** Even
  on RESOURCE_CONCENTRATION_NECESSARY, v0.43 only establishes that
  concentration-as-such is necessary at one hazard, on one seed
  band, under one intervention type. Mechanism specificity (which
  property of concentration carries the effect) requires v0.44+
  intervention refinement.
- **Effect-size budget.** Same threshold (0.15) and tolerance
  (0.10) as v0.42, on the same observable. Cross-version
  comparability is intentional.
- **B_flatten dilutes more than C_shuffle.** Flatten spreads the
  total food over `n_eligible_cells`, which is substantially larger
  than the original food zone. Per-cell food density drops sharply.
  Shuffle preserves the multiset, so per-cell-with-food density is
  unchanged in the cells that hold the reassigned values; only the
  *positions* change. This asymmetry is intentional and corresponds
  to the design: B tests concentration-as-density, C tests
  concentration-at-this-location. The auxiliary
  FLATTEN_ABLATES_REPRODUCTION finding addresses the dilution side-
  effect explicitly.

### Reachability — sanity check

All three primary verdicts plus the halt cell are arithmetically
reachable:

- **RESOURCE_CONCENTRATION_NECESSARY**: requires B share to drop by
  ≥ 0.15 from A AND C share to stay within ±0.10 of A. Both bars
  are independent and live; concentration-as-such would land here.
- **SUBSTRATE_REWRITE_DISRUPTS_DOMINANCE**: requires B share AND C
  share both to drop by ≥ 0.10–0.15 from A. If the system is
  fragile to any substrate-rewrite of comparable magnitude, this
  is where it lands.
- **RESOURCE_CONCENTRATION_NOT_NECESSARY**: requires B share to NOT
  drop by ≥ 0.15. If post-50 dominance reconstitutes regardless of
  food layout, this is where it lands.
- **C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT (halt)**: requires C
  share to rise above A by > 0.10 while B drops. Mechanistically
  unmotivated; halt loud, no scientific verdict emitted.

The rule space genuinely separates the three.

### Anchor identity

- v0.43 inherits no cross-version artifact-identity anchors against
  prior reducer outputs (its corpus is new). It does inherit two
  byte-identity anchors: re-running a sampled v0.42 A_null seed
  AND a sampled v0.42 B_kill_leader seed with v0.43 code must
  produce events.jsonl byte-identical to v0.42's sealed references
  (regression guards, H2e). These cover (a) the legacy null path
  and (b) the v0.42 kill paths.

## Decision rules

### Primary

| `b_passes` | C-direction             | verdict                                              |
|:----------:|-------------------------|------------------------------------------------------|
| True       | `c_passes` (|c−a|≤0.10) | **RESOURCE_CONCENTRATION_NECESSARY**                 |
| True       | `c_below_a` (c−a≤−0.10) | **SUBSTRATE_REWRITE_DISRUPTS_DOMINANCE**             |
| True       | `c_above_a` (c−a>+0.10) | **C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT** (halt)    |
| False      | any                     | **RESOURCE_CONCENTRATION_NOT_NECESSARY**             |

### Auxiliary (independent of primary)

`FLATTEN_ABLATES_REPRODUCTION` per hazard, fires iff
`b_n_excluded_zero_post50 > 2` at that hazard.

### Secondary (does not fire verdict; descriptive context only)

`hazard_amplified := abs(delta_b_minus_a_h8) > abs(delta_b_minus_a_h0)`.
Reports whether the substrate-necessity effect is hazard-amplified.
Strong hazard amplification + primary firing
(RESOURCE_CONCENTRATION_NECESSARY or
SUBSTRATE_REWRITE_DISRUPTS_DOMINANCE) is the strongest possible
result.

### Halt conditions

- **H1 fails** — v0.34..v0.42 reducer surface mutated, OR byte-
  identity regression test fails (sampled v0.42 A_null seed OR
  v0.42 B_kill_leader seed). Halt; revert.
- **H2a fails** — run count != 48. Halt.
- **H2b fails** — intervention fires per arm violate locked counts.
  Halt.
- **H2c fails** — `effective_tick` != 51 on any fired event. Halt.
- **H2d fails** — substrate conservation violated (total food drift
  or multiset corruption or hazard/wall topology change). Halt.
- **H2e fails** — sampled byte-identity regression fails. Halt.
- **H3 / H4 fail** — pre-v0.43 contract broken by v0.43 additions.
  Halt; revert.
- **C-rises-above-A cell** — substrate artefact unmodeled. Halt
  loud; do NOT silently bin into one of the three verdicts.

## Out of scope (v0.43)

- Sufficiency testing.
- Mechanism specificity (which property of concentration).
- Hazard generalisation beyond {0, 8}.
- Cross-stream calibration of the intervention beyond seeds 49..56.
- Cross-stream calibration of v0.42 (deferred candidate (j)).
- Hazard-relocation interventions.
- Chamber-geometry interventions (wall placement, reachability).
- Birth-suppression, energy-drain, spatial-relocation, sufficiency-
  injection interventions.
- HedonismPolicy comparisons.
- Mesa migration.
- Edits to existing v0.34..v0.42 reducer surface, audit, sweep, or
  pre-v0.43 arm tuples.
- Changes to existing chamber, policy, or population dynamics
  outside the intervention kind dispatch in
  `core/interventions.py`.

## Implementation notes

### File-level changes

- **Modified (in `src/`):**
  - `src/hedonism_harness/core/interventions.py` (~150 LOC added):
    extend `InterventionConfig.kind` Literal with two new values;
    add `_eligible_cells`,
    `_flatten_food_over_eligible_cells`,
    `_shuffle_food_over_eligible_cells`; extend
    `apply_intervention` dispatcher. **Existing `null` /
    `kill_tick50_leader` / `kill_size_matched_nonleader` paths
    untouched.**
  - `src/hedonism_harness/core/events.py` (~30 LOC added): one new
    `FoodRedistributedByIntervention` frozen dataclass; added to
    `_SIGNAL_NAMES` and `AnyEvent` union. **No new `DeathCause`
    value.**
  - `src/hedonism_harness/experiments/comparison_grid.py` (~30 LOC
    added): one new constant `V0_43_INTERVENTION_ARMS` (additive).
- **New (in `scripts/`):**
  - `scripts/v0.43_sweep.py` (~80 LOC, mirrors v0.42 sweep).
  - `scripts/v0_43_intervention_audit.py` (~600 LOC).
- **New (in `tests/`):**
  - `tests/test_interventions_v0_43.py` (~250 LOC):
    `_eligible_cells` selection; flatten preserves total food
    within tolerance; flatten sets kind correctly; shuffle preserves
    multiset; shuffle uses reverse-row-major over (x, y)-sorted
    eligible cells; both leave hazard and wall cells unchanged;
    determinism (same input → same output bytes).
  - `tests/test_world_intervention_hook_v0_43.py` (~100 LOC):
    extends v0.42's hook tests for the new kinds; byte-identity
    regression on a sampled v0.42 A_null seed and v0.42
    B_kill_leader seed.
  - `tests/test_v0_43_sweep.py` (~120 LOC).
  - `tests/test_v0_43_intervention_audit.py` (~500 LOC).
- **Documented:** this pre-reg. Results appended after the audit
  runs.
- **Manifest:** new file
  `docs/artifacts/v0.34_v0.43_local_corpus_manifest.md` post-
  Results. The v0.34_v0.42 manifest is preserved as a sealed
  historical record.

### Tests required (locked at pre-reg time)

- **Intervention extensions:**
  - `_eligible_cells` returns cells with kind in {EMPTY, FOOD},
    sorted by (x, y) ascending; excludes HAZARD, WALL.
  - `_flatten_food_over_eligible_cells` preserves total food within
    `TOTAL_FOOD_ABS_TOL` / `TOTAL_FOOD_REL_TOL`; sets every
    eligible cell's `food_value` to mean; sets `kind` to FOOD if
    mean > 0 else EMPTY; HAZARD and WALL cells unchanged.
  - `_shuffle_food_over_eligible_cells` preserves total food
    exactly; preserves multiset of `food_value` over eligible
    cells; reverse-row-major permutation correctness on a small
    synthetic chamber; HAZARD and WALL cells unchanged.
  - `apply_intervention` routes the new kinds correctly.
  - Determinism: same world state at firing → byte-identical post-
    state.
  - `kind="null"` remains byte-identical to default-None (v0.42
    invariant preserved).
- **World hook extension:**
  - `optional_intervention=InterventionConfig(kind="flatten_food_at_tick50")`
    fires at the correct tick boundary, emits exactly one
    `FoodRedistributedByIntervention` event with correct fields.
  - Same for `kind="shuffle_food_at_tick50"`.
  - Default `optional_intervention=None` produces byte-identical
    events.jsonl on a sampled v0.41 seed (regression).
  - `kind="null"` produces byte-identical events.jsonl on a
    sampled v0.42 A_null seed (regression).
  - `kind="kill_tick50_leader"` produces byte-identical
    events.jsonl on a sampled v0.42 B_kill_leader seed (regression).
- **Sweep:** locked constants, arm tuple, seeds, hazards.
- **Audit:** locked thresholds, all 5 H2 halts, primary/secondary/
  auxiliary test arithmetic, three-way verdict + halt cell, locked-
  phrase regression guards, end-to-end synthetic fixture.

### Determinism contract

- `_eligible_cells`, `_flatten_food_over_eligible_cells`, and
  `_shuffle_food_over_eligible_cells` are pure functions of
  tick-50 chamber state (kind_layer + food_value).
- No new RNG. No `model.streams` draws.
- Default-None hook path is byte-identical to pre-v0.42.
- `kind="null"` hook path is byte-identical to default-None.
- v0.42 kill paths byte-identical when re-run on v0.43 branch.
- Re-running v0.43 sweep with the same seeds produces byte-
  identical events.jsonl files.

### LOC estimate

- `interventions.py` extension: ~150 LOC.
- `events.py` extension: ~30 LOC.
- `comparison_grid.py` arm tuple: ~30 LOC.
- Sweep + audit: ~700 LOC.
- 4 test files: ~1,000 LOC.
- This doc: ~750 LOC.
- Manifest (post-Results): ~250 LOC.

Total v0.43: ~2,900 LOC. Tests should bring the suite from 1,295
to ~1,335 (+~40).

### CI gate at pre-reg time

```
uv run ruff check .             ok
uv run ruff format --check .    ok
uv run pytest                   1295 passed, 6 skipped (baseline)
uv run python scripts/core_smoke_test.py   ok
```

(Pre-reg adds no executable code; CI is identical to v0.42 close.)

## Results

**Status:** sweep NOT executed. Pre-reg halted pre-sweep on the
substrate feasibility finding documented in
SUBSTRATE_PREFLIGHT_HALT below. **No verdict is emitted from the
v0.43 design. In particular, no `RESOURCE_CONCENTRATION_NOT_NECESSARY`
conclusion is drawn — the design's primary test cannot fire
informatively because the intervention is a no-op at the primary
hazard.**

## SUBSTRATE_PREFLIGHT_HALT (2026-05-07)

> **RETRACTION NOTICE (added 2026-05-07, post-v0.43R halt):** the
> "saturated zone" characterization in this addendum is **incorrect
> and config-mismatched**. The feasibility probe that produced the
> 480.0-total-food finding was a hand-rolled `run_chamber` invocation
> that defaulted `policy_factory` to `HedonismPolicy` and
> `auto_reproduction` to `False` — neither matches the actual sweep
> config (V0_25 anchor: `GradientPolicy` + `auto_reproduction=True` +
> `TraitConfig(unbounded_mutation=True)`). With the actual config,
> the substrate at tick 50 is **depleted to zero**, not saturated.
> See [[docs/experiments/fear_hunger_v0.43R.md]]
> SUBSTRATE_PREFLIGHT_HALT_2 for the corrected substrate finding +
> the methodological lesson (always feasibility-probe through
> `_run_one_arm_seed`, never through hand-rolled `run_chamber`).
> The text below is preserved as the historical record of the
> incorrect characterization that informed v0.43R's design; the
> retracted claim should not be cited.

After the additive `src/` extension landed (`core/events.py` +
`core/interventions.py` + `comparison_grid.py` arms; tests passing)
but **before** running the v0.43 sweep, a substrate feasibility
probe was run with the locked v0.43 eligibility predicate
(`kind ∈ {EMPTY, FOOD}` at tick 50) across the full v0.43 seed
band 49..56 at both hazards.

### Probe finding

The `tight_gradient` chamber is fully painted: every cell is
exactly one of {SAFE, HAZARD, FOOD}. There are no untyped EMPTY
cells outside the food zone. The eligible footprint is therefore
the food zone itself (24 cells), modulo any cells inside the zone
whose kind has flipped to EMPTY from a recent EAT action.

Per-hazard tick-50 substrate composition across seeds 49..56
(measured via tick observer; eligibility predicate verbatim from
the v0.43 implementation):

| hazard | n_empty (in zone) | n_food (in zone) | total food | flatten mean | expected n_cells_changed | expected EMPTY→FOOD | expected FOOD-reduce |
|---|---|---|---|---|---|---|---|
| 0 | 5–14 | 10–19 | 200–380 | 8.3–15.8 | **24 every seed** | 5–14 | 10–19 |
| 8 | **0** every seed | **24** every seed | **480** every seed | 20.0 | **0** every seed | 0 | 0 |

At **h=8**, the food zone is saturated at tick 50 across all 8
probed seeds (total food = 24 × 20.0 = 480.0). Flatten and shuffle
are **both no-ops at the primary test hazard**: every eligible
cell already holds the mean, the multiset is preserved trivially.
The locked primary test (`b_share_h8 ≤ a_share_h8 - 0.15`) cannot
distinguish B from A because their events.jsonl after tick 51 is
byte-identical.

At **h=0**, the substrate is heterogeneous (5–14 EMPTY cells in
the zone from recent consumption); flatten is operative. But the
v0.42 negative result was at h=8, which is the post-v0.42 target;
shifting the primary to h=0 is not the right move (it dodges the
post-v0.42 question).

### Cause

`food_respawn_cooldown=50`: a cell eaten at tick T flips to FOOD
again at tick T+50. By tick 50, any cell eaten at tick 0 has just
refilled. At h=8, agents avoid the hazard zone aggressively, food
zone consumption is low, and respawn keeps up with consumption →
all 24 cells either uneaten or already refilled at tick 50.

### What this halt preserves

- The pre-reg's locked phrases for
  `RESOURCE_CONCENTRATION_NECESSARY` /
  `SUBSTRATE_REWRITE_DISRUPTS_DOMINANCE` /
  `RESOURCE_CONCENTRATION_NOT_NECESSARY` remain unfired. **None of
  these phrases applies to a sweep that was never run**, and
  applying them post-hoc to a no-op intervention would be a
  silent repurpose.
- The additive `src/` extension (`FoodRedistributedByIntervention`
  event, `KIND_FLATTEN_FOOD` / `KIND_SHUFFLE_FOOD` kinds, the
  `_eligible_cells` / `_flatten_food_over_eligible_cells` /
  `_shuffle_food_over_eligible_cells` helpers) is **preserved**.
  All v0.42 tests + 27 new v0.43 unit tests still pass. The
  primitives are reusable for the v0.43R replacement pre-reg.
- The `V0_43_INTERVENTION_ARMS` constant is **preserved** for the
  same reason.

### What the halt rules out scientifically

- The v0.43 design as locked cannot test the
  "tick-50 chamber-wide food-flatten" question on `tight_gradient`
  at h=8. There is no eligible chamber-wide substrate beyond the
  saturated food zone for the intervention to operate on.
- The v0.43 design's `_eligible_cells` predicate is **literally
  correct** w.r.t. its locked text (`kind ∈ {EMPTY, FOOD}`); the
  scientific intent ("destroy chamber-wide food concentration")
  assumed an EMPTY footprint outside the zone that does not exist
  in `tight_gradient`'s painted layout.

### Substrate-state finding — first-class result of the halt

> **At the v0.34..v0.42 anchor moment (tick 50) under
> `tight_gradient` + `food_respawn_cooldown=50` + `hazard_damage=8`,
> the food zone is at maximum density across all probed seeds.**
> The post-50 dominance pattern observed in v0.34..v0.41 emerges
> from a substrate where, at the locking tick, food concentration
> IS at its maximum. Whatever drives the dominance pattern reads
> off a saturated food substrate, not a depleted or heterogeneous
> one. This is descriptive context, not a verdict.

### Replacement pre-reg track (v0.43R candidate)

Two operational variants under consideration. Both preserve
`tight_gradient` chamber, `food_respawn_cooldown=50`, hazards
{0, 8}, seeds 49..56:

1. **Early-flatten variant.** Move the intervention boundary
   earlier (candidate tick 25/26), where the substrate is still
   heterogeneous before respawn saturates. Tests:
   "Is pre-anchor food-substrate disruption necessary for later
   post-50 dominance?" Note: this is a question-shift, not a
   parameter-shift — it intervenes on the trajectory, not on the
   anchor moment.
2. **Density-reduction-at-tick-50 variant.** Keep the tick-50
   anchor for clean v0.42 comparability; instead of flattening,
   multiply every eligible cell's `food_value` by a fixed factor
   (e.g., 0.5). Multiset shifts, total drops, kind topology
   preserved. Tests: "Is **food density** at tick 50 necessary
   for post-50 dominance?" — concentration-as-magnitude rather
   than concentration-as-spatial-gradient. Operative at h=8 (480
   → 240; every cell changes).

A broader feasibility probe (ticks 20/25/30/35 + density-reduction
at tick 50) will run before locking the v0.43R design. The chosen
variant will be locked in a NEW pre-reg
(`docs/experiments/fear_hunger_v0.43R.md` or similar), not by
editing this one. The v0.43 pre-reg stands as the historical
record of the halted design.
